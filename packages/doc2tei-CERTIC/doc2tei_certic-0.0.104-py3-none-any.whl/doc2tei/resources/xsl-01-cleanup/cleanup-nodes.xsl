<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"		
  exclude-result-prefixes="formx config of svg dr3d calcext loext form field script chart">
    
<!-- ##FIGURES## -->
<!-- Conservation des informations de mise en formes des tableaux & cellules -->
<xsl:template match="office:automatic-styles">
    <xsl:choose>
        <xsl:when test="child::style:style[@style:family='table']">
            <office:automatic-styles>
                <xsl:copy-of select="child::style:style[@style:family='table-cell']"/>
            </office:automatic-styles>            
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>

<xsl:template match="draw:image">
  <xsl:variable name="xmlFolder">
    <xsl:for-each select="tokenize(substring-after(document-uri(/),'file:'),'/')">
      <xsl:choose>
        <xsl:when test="position()!=last()">
          <xsl:value-of select="."/>
          <xsl:text>/</xsl:text>
        </xsl:when>
      </xsl:choose>
    </xsl:for-each>
  </xsl:variable>
    
  <!-- Lien relatif vers les images -->
  <xsl:variable name="imagePath">
      <xsl:value-of select="concat('images/image-',count(preceding::draw:frame)+1)"/>
    <xsl:choose>
      <xsl:when test="@*:mime-type='image/jpeg'">
        <xsl:text>.jpg.base64</xsl:text>
      </xsl:when>
      <xsl:when test="@*:mime-type='image/png'">
        <xsl:text>.png.base64</xsl:text>
      </xsl:when>
      <xsl:when test="@*:mime-type='image/gif'">
        <xsl:text>.gif.base64</xsl:text>
      </xsl:when>
      <xsl:when test="@*:mime-type='image/svg+xml'">
        <xsl:text>.svg.base64</xsl:text>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>

  <xsl:choose>
    <!-- Images incluses par une référence (lien) -->
    <xsl:when test="not(office:binary-data)">
      <xsl:copy-of select="."/>
    </xsl:when>
    <!-- Images embarquées dans le document -->
    <xsl:when test="@*:mime-type='image/jpeg' or @*:mime-type='image/png' or @*:mime-type='image/gif' or @*:mime-type='image/svg+xml'">
      <xsl:if test="not(preceding-sibling::draw:image[1][@*:mime-type='image/svg+xml'])">
        <draw:image xlink:href="{substring-before($imagePath,'.base64')}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad" loext:mime-type="{@*:mime-type}"/>
        <xsl:choose>
            <xsl:when test="$source='OpenEdition'">
              <xsl:result-document href="{concat($xmlFolder,$imagePath)}" omit-xml-declaration="yes">
                  <xsl:value-of select="./office:binary-data"/>
                </xsl:result-document>
            </xsl:when>
            <xsl:otherwise/>
          </xsl:choose>
      </xsl:if>
    </xsl:when>
    <!-- cas équation Math ML doc Word -->
    <xsl:when test="preceding-sibling::*[1][local-name()='object' and child::*/local-name()='math']"></xsl:when>
    <!-- Formats d'image non traités -->
    <xsl:otherwise>
      <ERROR>
          <xsl:text>FATAL : IMAGE FORMAT (</xsl:text>
          <xsl:value-of select="./@*:mime-type"/>
          <xsl:text>) NOT SUPPORTED</xsl:text>
      </ERROR>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template match="@draw:style-name"/>
<xsl:template match="@draw:z-index"/>    
<xsl:template match="@svg:height"/>
<xsl:template match="@svg:width"/>
<xsl:template match="@text:anchor-type"/>
<xsl:template match="@xlink:actuate"/>
<xsl:template match="@xlink:show"/>
<xsl:template match="@xlink:type"/>
    
<!-- ##LISTES## -->
<!-- les listes imbriquées : n'ont pas d'@ donc template dédié -->
<xsl:template match="text:list[not(@text:style-name)]">
    <xsl:variable name="listDepth">
        <xsl:value-of select="count(ancestor::text:list)+1"/>
    </xsl:variable>
    <xsl:variable name="listStyle">
        <xsl:value-of select="ancestor-or-self::text:list/@text:style-name"/>
    </xsl:variable>
    <xsl:element name="text:list">
        <xsl:copy-of select="@*"/>
        <xsl:attribute name="type">
            <xsl:choose>
                <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][local-name()='list-level-style-number']">ordered</xsl:when>
                <xsl:otherwise>unordered</xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
        <xsl:choose>
            <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@style:num-format]">
                <xsl:copy-of select="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth]/@style:num-format"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="text:bullet-char">
                    <xsl:choose>
                        <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@text:bullet-char=''][child::style:text-properties[@fo:font-family='Symbol']]">●</xsl:when>
                        <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@text:bullet-char=''][child::style:text-properties[@fo:font-family='Wingdings']]">■</xsl:when>
                        <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@text:bullet-char='o'][child::style:text-properties[contains(@fo:font-family,'Courier New')]]">○</xsl:when>
                        <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@text:bullet-char='-'][child::style:text-properties[contains(@fo:font-family,'Calibri')]]">-</xsl:when>
                        <xsl:when test="preceding::text:list-style[@style:name=$listStyle]/child::*[@text:level=$listDepth][@text:bullet-char='–'][child::style:text-properties[contains(@fo:font-family,'Calibri')]]">-</xsl:when>
                        <xsl:otherwise>??</xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>   
        <xsl:apply-templates/>
    </xsl:element>
</xsl:template>
    
</xsl:stylesheet>