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
  xmlns="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="#all">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>
<xsl:strip-space elements="draw:frame"/>
<!-- TODO
- ajouter le traitement des tétiêres
- ajouter le traitement des fusions
- ajouter le renvoi aux propriétés CSS (?)
-->
    
    
<!-- ## TABLES ## -->
<xsl:template match="table:table[parent::*:figure]">
<xsl:variable name="tableColumn">
  <xsl:choose>
    <xsl:when test="child::table:table-column/@table:number-columns-repeated and child::table:table-column[not(@table:number-columns-repeated)]">
      <xsl:value-of select="sum(child::table:table-column/@table:number-columns-repeated) + count(child::table:table-column[not(@table:number-columns-repeated)])"/>
    </xsl:when>
    <xsl:when test="child::table:table-column[not(@table:number-columns-repeated)]">
      <xsl:value-of select="count(child::table:table-column)"/>
    </xsl:when>
    <xsl:when test="child::table:table-column/@table:number-columns-repeated">
      <xsl:value-of select="sum(child::table:table-column/@table:number-columns-repeated)"/>
    </xsl:when>
    <xsl:otherwise/>
  </xsl:choose>
</xsl:variable>

    <table>
        <xsl:attribute name="xml:id" select="@table:name"/>
        <xsl:attribute name="rows" select="count(descendant::table:table-row)"/>
        <xsl:attribute name="cols" select="$tableColumn"/>
        <xsl:apply-templates/>
    </table>
</xsl:template>
    
<xsl:template match="table:table[not(parent::*:figure)]">
<xsl:variable name="tableColumn">
  <xsl:choose>
    <xsl:when test="child::table:table-column/@table:number-columns-repeated and child::table:table-column[not(@table:number-columns-repeated)]">
      <xsl:value-of select="sum(child::table:table-column/@table:number-columns-repeated) + count(child::table:table-column[not(@table:number-columns-repeated)])"/>
    </xsl:when>
    <xsl:when test="child::table:table-column[not(@table:number-columns-repeated)]">
      <xsl:value-of select="count(child::table:table-column)"/>
    </xsl:when>
    <xsl:when test="child::table:table-column/@table:number-columns-repeated">
      <xsl:value-of select="sum(child::table:table-column/@table:number-columns-repeated)"/>
    </xsl:when>
    <xsl:otherwise/>
  </xsl:choose>
</xsl:variable>
  <figure>
    <table>
        <xsl:attribute name="xml:id" select="@table:name"/>
        <xsl:attribute name="rows" select="count(descendant::table:table-row)"/>
        <xsl:attribute name="cols" select="$tableColumn"/>
        <xsl:apply-templates/>
    </table>
  </figure>
</xsl:template>
    
<xsl:template match="table:table-header-rows">
    <xsl:apply-templates/>
</xsl:template>

<xsl:template match="table:table-header-rows/table:table-row">
    <row role="label">
      <xsl:apply-templates/>
    </row>
  </xsl:template>
    
<xsl:template match="table:table-row">
    <row>
        <xsl:apply-templates/>
    </row>
</xsl:template>
    
<xsl:template match="table:table-cell">
    <cell>
        <xsl:if test="@table:number-columns-spanned &gt;'1'">
          <xsl:attribute name="cols">
            <xsl:value-of select="@table:number-columns-spanned"/>
          </xsl:attribute>
        </xsl:if>
        <xsl:if test="@table:number-rows-spanned &gt;'1'">
          <xsl:attribute name="rows">
            <xsl:value-of select="@table:number-rows-spanned"/>
          </xsl:attribute>
        </xsl:if>
        <xsl:attribute name="rendition">
            <!-- Tableau, Tabla, Table, Tabella,  -->
            <xsl:variable name="tableLang">
                <xsl:choose>
                    <xsl:when test="contains(@table:style-name,'Tableau')">Tableau</xsl:when>
                    <xsl:when test="contains(@table:style-name,'Tabla')">Tabla</xsl:when>
                    <xsl:when test="contains(@table:style-name,'Table')">Table</xsl:when>
                    <xsl:when test="contains(@table:style-name,'Tabella')">Tabella</xsl:when>
                    <xsl:when test="contains(@table:style-name,'Tabela')">Tabela</xsl:when>
                </xsl:choose>
            </xsl:variable>
            <xsl:value-of select="concat('#Cell',substring-after(@table:style-name,$tableLang))"/>
  	     </xsl:attribute>
        <xsl:choose>
            <xsl:when test="child::text:p[@text:style-name='Standard']">
                <xsl:choose>
                    <xsl:when test="count(child::text:p) &gt; 1">
                        <xsl:apply-templates/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="child::text:p[@text:style-name='Standard']/@rendition">
                                <p>
                                    <xsl:copy-of select="child::text:p[@text:style-name='Standard']/@rendition"/>
                                    <xsl:apply-templates select="child::text:p[@text:style-name='Standard']/node()"/>
                                </p>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:apply-templates select="child::text:p[@text:style-name='Standard']/node()"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </cell>
</xsl:template>

<!--<xsl:template match="text:p[@text:style-name='TEI_cell']"/>-->
<xsl:template match="table:table-column"/>
<xsl:template match="table:covered-table-cell"/>

<xsl:template match="text:p[@text:style-name='TEI_figure_alternative']">
    <graphic type="alternative">
        <xsl:attribute name="url">
            <xsl:choose>
                <xsl:when test="$source='Metopes'">
                    <xsl:value-of select="concat('../icono',substring-after(descendant::draw:image/@xlink:href,'icono'))"/>
                </xsl:when>
                <xsl:otherwise><xsl:value-of select="descendant::draw:image/@xlink:href"/></xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </graphic>
    <xsl:apply-templates select="descendant::svg:desc"/>
</xsl:template>

<!-- ## FIGURES ## -->
<xsl:template match="text:p[@text:style-name='TEI_figure_title']">
    <head>
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:if test="@xml:lang != substring($mainLang,1,2)">
            <xsl:attribute name="type">trl</xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </head>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_figure_caption']">
    <p rend="caption"><xsl:copy-of select="@xml:lang|@rendition"/><xsl:apply-templates/></p>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_figure_credits']">
    <p rend="credits"><xsl:copy-of select="@xml:lang|@rendition"/><xsl:apply-templates/></p>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_figure_credits_inline']">
    <desc><xsl:apply-templates/></desc>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_figure_source_inline']">
    <bibl rend="inline"><xsl:apply-templates/></bibl>
 </xsl:template>
    
    <xsl:template match="text:span[@text:style-name='TEI_figure_num_inline']">
        <num><xsl:apply-templates/></num>
    </xsl:template>
    
<xsl:template match="draw:frame">
    <xsl:choose>
        <xsl:when test="preceding-sibling::text() or following-sibling::text()">
            <figure rend="inline"><xsl:apply-templates/></figure>
        </xsl:when>
        <xsl:when test="ancestor::*:figure and not(ancestor::table:table-cell)">
            <xsl:apply-templates/>
        </xsl:when>
        <!-- dans une cellule de tableau : sans texte avant ou après donc block mais peut déjà être dans une section figure (avec titre, légende…) -->
        <xsl:when test="not(preceding-sibling::text() or following-sibling::text()) and ancestor::table:table-cell">
            <xsl:choose>
                <xsl:when test="parent::text:p[parent::*:figure]">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <figure><xsl:apply-templates/></figure>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:when test="child::table:table">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:when test="not(preceding-sibling::text() or following-sibling::text()) and parent::text:p[parent::text:note]">
            <figure><xsl:apply-templates/></figure>
        </xsl:when>
        <xsl:otherwise>
            <xsl:apply-templates/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="draw:image">
    <!-- ici pour insertion de l'élément figure dans les cas inline et block seul -->
    <xsl:element name="graphic" xmlns="http://www.tei-c.org/ns/1.0">
        <xsl:attribute name="url">
            <xsl:choose>
                <xsl:when test="$source='Metopes'">
                    <xsl:value-of select="concat('../icono',substring-after(@xlink:href,'icono'))"/>
                </xsl:when>
                <xsl:otherwise><xsl:value-of select="@xlink:href"/></xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </xsl:element>
</xsl:template>
    
<xsl:template match="svg:desc">
    <xsl:choose>
      <xsl:when test="$source='Metopes'">
            <figDesc><xsl:apply-templates/></figDesc>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_figure_alttext']">
    <xsl:choose>
      <xsl:when test="$source='OpenEdition'">
            <figDesc><xsl:value-of select="."/></figDesc>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>
    
<!-- ## FORMULA ## -->

<!-- mathML -->
<xsl:template match="draw:frame[child::draw:object]">
    <xsl:choose>
        <!-- cas block complexe -->
        <xsl:when test="ancestor::*:figure">
            <formula notation="mml"><xsl:apply-templates/></formula>
        </xsl:when>
        <!-- cas block simple -->
        <xsl:when test="parent::text:p[@text:style-name='TEI_formula']">
            <figure><formula notation="mml"><xsl:apply-templates/></formula></figure>
        </xsl:when>
        <xsl:otherwise>
            <figure rend="inline">
                <formula notation="mml">
                        <math  xmlns="http://www.w3.org/1998/Math/MathML" display="inline">
                    <xsl:apply-templates select="child::draw:object/*:math/node()"/>
                        </math>
                </formula>
            </figure>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="draw:frame/draw:object">
    <xsl:apply-templates/>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_formula']">
    <xsl:choose>
        <xsl:when test="child::draw:frame[child::draw:object]">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:when test="not(parent::*:figure)">
            <figure>
                <formula notation="latex"><xsl:apply-templates/></formula>
            </figure>
        </xsl:when>
        <xsl:otherwise>
            <formula notation="latex"><xsl:apply-templates/></formula>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_formula-inline']">
    <figure rend="inline"><formula notation="latex"><xsl:apply-templates/></formula></figure>
</xsl:template>

<!--<xsl:template match="endOfDocument"/>-->

</xsl:stylesheet>